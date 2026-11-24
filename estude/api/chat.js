// Função serverless da Vercel: fala com a Groq.
// A chave NUNCA vai para o navegador: ela fica na variável de ambiente GROQ_API_KEY.
//
// Variáveis de ambiente (Vercel > Settings > Environment Variables):
//   GROQ_API_KEY  (obrigatória)  chave criada em console.groq.com
//   GROQ_MODEL    (opcional)     padrão: openai/gpt-oss-120b

const MATERIAS = {
  artes: require('../content/artes.json'),
};

const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const MODEL = process.env.GROQ_MODEL || 'openai/gpt-oss-120b';

// Limite simples por IP (vale por instância da função; é só uma proteção básica).
const JANELA_MS = 60 * 1000;
const MAX_POR_JANELA = 15;
const acessos = new Map();

function limitado(ip) {
  const agora = Date.now();
  const lista = (acessos.get(ip) || []).filter((t) => agora - t < JANELA_MS);
  lista.push(agora);
  acessos.set(ip, lista);
  if (acessos.size > 500) acessos.clear();
  return lista.length > MAX_POR_JANELA;
}

function promptSistema(m, modo) {
  const base =
    `Você é o assistente de estudos de um aluno do ensino fundamental, na matéria de ${m.materia}. ` +
    `Responda SEMPRE em português do Brasil, com linguagem simples, curta e amigável. ` +
    `Não invente informações: se não tiver certeza, diga que não tem certeza.\n\n` +
    `MATERIAL DA MATÉRIA (tópico: ${m.topico}):\n"""\n${m.material}\n"""\n\n`;

  if (modo === 'resumo') {
    return (
      base +
      `Tarefa: faça um RESUMO organizado do material acima, só com o que está nele. ` +
      `Use este formato em markdown simples:\n` +
      `## Resumo\n(2 a 4 frases)\n` +
      `## Ideias principais\n(lista com "- ", cada item curto)\n` +
      `## Palavras importantes\n(lista "- **palavra**: significado simples")\n` +
      `## Para lembrar na prova\n(3 dicas curtas em lista)\n`
    );
  }

  return (
    base +
    `Tarefa: tirar dúvidas do aluno sobre ${m.materia}. ` +
    `Use o material acima como base principal. Se a dúvida for da matéria mas não estiver no material, ` +
    `explique de forma geral e avise que isso não está no material. ` +
    `Se o assunto não tiver nada a ver com estudar ${m.materia}, diga com gentileza que só pode ajudar com essa matéria. ` +
    `Quando fizer sentido, dê um exemplo curto. Não escreva textos enormes. ` +
    `Se o aluno pedir um quiz, faça UMA pergunta por vez e espere a resposta.`
  );
}

function lerJson(corpo) {
  if (corpo && typeof corpo === 'object') return corpo;
  try {
    return JSON.parse(corpo || '{}');
  } catch {
    return {};
  }
}

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');

  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ erro: 'Método não permitido.' });
  }

  const chave = process.env.GROQ_API_KEY;
  if (!chave) {
    return res.status(500).json({
      erro: 'A chave GROQ_API_KEY ainda não foi configurada na Vercel (Settings > Environment Variables).',
    });
  }

  const ip = String(req.headers['x-forwarded-for'] || 'anon').split(',')[0].trim();
  if (limitado(ip)) {
    return res.status(429).json({ erro: 'Calma! Muitas perguntas seguidas. Espere um minutinho e tente de novo.' });
  }

  const body = lerJson(req.body);
  const materia = MATERIAS[body.materia];
  if (!materia) return res.status(400).json({ erro: 'Matéria inválida.' });

  const modo = body.modo === 'resumo' ? 'resumo' : 'chat';

  if (!materia.material || materia.material.trim().length < 20) {
    return res.status(400).json({ erro: 'O material desta matéria ainda não foi adicionado.' });
  }

  let mensagens;
  if (modo === 'resumo') {
    mensagens = [{ role: 'user', content: 'Faça o resumo do material.' }];
  } else {
    const lista = Array.isArray(body.mensagens) ? body.mensagens : [];
    mensagens = lista
      .filter((m) => m && (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string')
      .slice(-12)
      .map((m) => ({ role: m.role, content: m.content.slice(0, 1500) }));
    if (!mensagens.length || mensagens[mensagens.length - 1].role !== 'user') {
      return res.status(400).json({ erro: 'Envie uma pergunta.' });
    }
  }

  const payload = {
    model: MODEL,
    messages: [{ role: 'system', content: promptSistema(materia, modo) }, ...mensagens],
    temperature: modo === 'resumo' ? 0.3 : 0.5,
    max_completion_tokens: modo === 'resumo' ? 1500 : 1000,
  };
  if (MODEL.startsWith('openai/gpt-oss')) payload.reasoning_effort = 'low';

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 25000);

  try {
    const r = await fetch(GROQ_URL, {
      method: 'POST',
      headers: { Authorization: `Bearer ${chave}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: ctrl.signal,
    });

    if (!r.ok) {
      const detalhe = await r.text().catch(() => '');
      console.error('Groq erro', r.status, detalhe.slice(0, 500));
      if (r.status === 429) {
        return res.status(429).json({ erro: 'A IA está ocupada agora. Tente de novo em instantes.' });
      }
      if (r.status === 401) {
        return res.status(500).json({ erro: 'A chave da Groq é inválida. Confira GROQ_API_KEY na Vercel.' });
      }
      return res.status(502).json({ erro: 'A IA não respondeu direito. Tente de novo.' });
    }

    const data = await r.json();
    let texto = (data && data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content) || '';
    texto = texto.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
    if (!texto) return res.status(502).json({ erro: 'A IA devolveu uma resposta vazia. Tente de novo.' });

    return res.status(200).json({ resposta: texto });
  } catch (e) {
    console.error('Falha ao chamar a Groq', e && e.message);
    const demorou = e && e.name === 'AbortError';
    return res.status(504).json({ erro: demorou ? 'A IA demorou demais. Tente de novo.' : 'Não consegui falar com a IA agora.' });
  } finally {
    clearTimeout(timer);
  }
};
