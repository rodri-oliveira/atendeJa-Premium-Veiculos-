import 'dotenv/config';
import axios from 'axios';
import qrcode from 'qrcode-terminal';
import pkg from 'whatsapp-web.js';
const { Client, LocalAuth } = pkg;
import QRCode from 'qrcode';

// Env
const MCP_URL = process.env.MCP_URL || 'http://localhost:8001/mcp/execute';
const MCP_TOKEN = process.env.MCP_TOKEN || '';
const TENANT_ID = process.env.MCP_TENANT_ID || 'default';
const SESSION_NAME = process.env.WA_SESSION_NAME || 'adapter-wa';
const WA_QR_FILE = process.env.WA_QR_FILE || 'qr.png';

// WhatsApp client
const client = new Client({
  authStrategy: new LocalAuth({ clientId: SESSION_NAME }),
  puppeteer: {
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  }
});

client.on('qr', (qr) => {
  console.log('\n[WA] Escaneie o QR code abaixo com o WhatsApp do cliente (Apenas para POC):');
  qrcode.generate(qr, { small: true });
  // Além do terminal, gera um PNG local para facilitar o scan
  QRCode.toFile(WA_QR_FILE, qr, { width: 320 }, (err) => {
    if (err) {
      console.error('[WA] Falha ao salvar QR em PNG:', err.message);
    } else {
      console.log(`[WA] QR salvo em arquivo: ${WA_QR_FILE}. Abra a imagem e escaneie.`);
    }
  });
});

client.on('ready', () => {
  console.log('[WA] Conectado. Sessão ativa.');
});

client.on('disconnected', (reason) => {
  console.log('[WA] Desconectado:', reason);
});

// Rate limit simples por contato
const lastMsgAt = new Map();
const PER_CONTACT_SECONDS = Number(process.env.WA_RATE_LIMIT_PER_CONTACT_SECONDS || 2);

function canReplyFor(contact) {
  const now = Date.now();
  const prev = lastMsgAt.get(contact) || 0;
  if (now - prev < PER_CONTACT_SECONDS * 1000) return false;
  lastMsgAt.set(contact, now);
  return true;
}

async function sendToMCP(text) {
  const body = {
    input: text,
    mode: 'tool',
    tool: 'pan_pre_analise',
    params: {},
    tenant_id: TENANT_ID
  };
  const headers = { 'Content-Type': 'application/json' };
  if (MCP_TOKEN) headers['Authorization'] = `Bearer ${MCP_TOKEN}`;
  const resp = await axios.post(MCP_URL, body, { headers, timeout: 10000 });
  return resp.data;
}

async function processAndReply({ text, chatId, reply }) {
  if (!canReplyFor(chatId)) return;
  const body = (text || '').trim();
  const lower = body.toLowerCase();

  if (lower === 'sair') {
    await reply('Ok! Encerrando por aqui.');
    return;
  }

  // Coleta CPF e categoria
  const cpfMatch = body.replace(/[^0-9]/g, '').match(/\d{11}/);
  const catMatch = lower.includes('usado') ? 'USADO' : (lower.includes('novo') ? 'NOVO' : undefined);

  let params = {};
  if (cpfMatch) params.cpf = cpfMatch[0];
  if (catMatch) params.categoria = catMatch;

  if (!params.cpf) {
    await reply('POC Pan • Envie seu CPF (ex: cpf 00000000000). Para sair: digite SAIR.');
    return;
  }
  if (!params.categoria) params.categoria = process.env.PAN_DEFAULT_CATEGORIA || 'USADO';

  const response = await axios.post(
    MCP_URL,
    { input: '', mode: 'tool', tool: 'pan_pre_analise', params, tenant_id: TENANT_ID },
    { headers: { 'Content-Type': 'application/json', ...(MCP_TOKEN ? { Authorization: `Bearer ${MCP_TOKEN}` } : {}) }, timeout: 10000 }
  );

  const data = response.data;
  const tc = Array.isArray(data.tool_calls) ? data.tool_calls[0] : null;
  const result = tc?.result || {};
  const payload = result.data || {};

  const resumo = `Resultado (POC):\n` +
    `• CPF: ${payload.cpf || '***'}\n` +
    `• Categoria: ${payload.categoriaVeiculo || params.categoria}\n` +
    `• Status: ${payload.resultado || (result.ok ? 'OK' : 'ERRO')}\n` +
    `• Limite: R$ ${payload.limite_pre_aprovado ?? 0}`;

  await reply(resumo);
}

client.on('message', async (msg) => {
  try {
    if (!msg.from || msg.from.endsWith('@g.us')) return; // ignora grupos
    console.log('[WA] Mensagem recebida de', msg.from, 'conteúdo:', msg.body);
    await processAndReply({ text: msg.body, chatId: msg.from, reply: (t) => msg.reply(t) });
  } catch (err) {
    console.error('[Adapter] erro ao processar mensagem:', err?.response?.data || err?.message || err);
    try { await msg.reply('Desculpe, ocorreu um erro temporário. Tente novamente.'); } catch {}
  }
});

// Suporte a mensagens para si mesmo (fromMe): usar message_create
client.on('message_create', async (msg) => {
  try {
    if (!msg.fromMe) return; // apenas mensagens enviadas por você
    // Quando é para si mesmo, responder no mesmo chat (msg.to)
    const target = msg.to || msg.from;
    console.log('[WA] message_create fromMe. to=', target, 'body=', msg.body);
    await processAndReply({ text: msg.body, chatId: target, reply: (t) => client.sendMessage(target, t) });
  } catch (err) {
    console.error('[Adapter] erro em message_create:', err?.response?.data || err?.message || err);
  }
});

client.initialize();
