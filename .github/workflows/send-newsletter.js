const axios = require('axios');
const translations = require('./translations');
const languageConfig = [
  {
    lang: 'pt',
    groupId: '160388108749112929',
    subject: process.env.NEWSLETTER_SUBJECT_PT,
    message: process.env.NEWSLETTER_MESSAGE_PT
  },
  {
    lang: 'en',
    groupId: '160526087389971585',
    subject: process.env.NEWSLETTER_SUBJECT_EN,
    message: process.env.NEWSLETTER_MESSAGE_EN
  },
  {
    lang: 'es',
    groupId: '160525869751731741',
    subject: process.env.NEWSLETTER_SUBJECT_ES,
    message: process.env.NEWSLETTER_MESSAGE_ES
  }
];
const API_KEY = process.env.MAILERLITE_API_KEY;
async function createAndSendCampaignForLanguage(config) {
  if (!config.groupId || !config.subject || !config.message) {
    console.log(`A saltar a língua '${config.lang}' por falta de configuração.`);
    return;
  }
  console.log(`\n--- A preparar newsletter para a língua: ${config.lang.toUpperCase()} ---`);
  const t = translations[config.lang];
  const emailHtmlContent = `
    <h1>${t.title}</h1>
    ${t.intro(config.message)}
    <p>${t.call_to_action}</p>
    <a href="https://manmaxim0.github.io/Bia/" style="background-color: #0056b3; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">${t.button}</a>
    <p style="font-size: 12px; color: #888; margin-top: 20px;">${t.footer}</p>
  `;
  const headers = {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  };
  const payload = {
    name: `${config.subject} (${config.lang.toUpperCase()})`,
    type: 'regular',
    groups: [config.groupId],
    emails: [{
      subject: config.subject,
      from_name: 'Beatriz Rodrigues',
      from: 'luisfmaximo8@gmail.com',
      content: emailHtmlContent
    }]
  };
  try {
    console.log(`A criar campanha para o grupo ${config.groupId}...`);
    const campaignResponse = await axios.post('https://connect.mailerlite.com/api/campaigns', payload, { headers });
    const campaignId = campaignResponse.data.data.id;
    console.log(`SUCESSO! Campanha (${config.lang}) criada com ID: ${response.data.data.id}`);
    console.log(`A emitir comando de envio para a campanha ${campaignId}...`);
    await axios.post(`https://connect.mailerlite.com/api/campaigns/${campaignId}/schedule`, {
      delivery: 'instant'
    }, { headers });
    console.log(`Comando de envio para a campanha (${config.lang}) emitido com sucesso!`);

  } catch (error) {
    console.error(`Ocorreu um erro ao enviar para a língua '${config.lang}':`);
    if (error.response) {
      console.error('Dados do Erro:', JSON.stringify(error.response.data, null, 2));
    } else {
      console.error('Mensagem de Erro:', error.message);
    }
  }
}

async function sendAllNewsletters() {
  if (!API_KEY) {
    console.error('Erro: A variável de ambiente MAILERLITE_API_KEY está em falta.');
    process.exit(1);
  }
  for (const config of languageConfig) {
    await createAndSendCampaignForLanguage(config);
  }
  console.log('\nProcesso de envio de newsletters concluído.');
}

sendAllNewsletters();