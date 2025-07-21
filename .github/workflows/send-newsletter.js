const axios = require('axios');
const API_KEY = process.env.MAILERLITE_API_KEY;

// Vamos usar valores fixos para o teste
const TEST_GROUP_ID = '160388108749112929'; // O ID do seu grupo PT
const TEST_SUBJECT = 'Campanha de Teste Simples';
const TEST_NAME = `Teste - ${new Date().toISOString()}`;
const TEST_HTML_CONTENT = '<p>Isto é um simples teste.</p>';

async function runTest() {
  if (!API_KEY) {
    console.error('Erro: A MAILERLITE_API_KEY está em falta.');
    process.exit(1);
  }

  console.log('--- A iniciar o teste de envio para o MailerLite ---');
  const headers = {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  };

  try {
    // PASSO 1: Criar a campanha com dados simples e fixos
    const campaignPayload = {
      name: TEST_NAME,
      type: 'regular',
      groups: [TEST_GROUP_ID]
    };
    
    console.log('A tentar criar campanha de teste com os seguintes dados:', JSON.stringify(campaignPayload));
    const campaignResponse = await axios.post('https://connect.mailerlite.com/api/campaigns', campaignPayload, { headers });
    const campaignId = campaignResponse.data.data.id;
    console.log(`SUCESSO no PASSO 1! Campanha de teste criada com ID: ${campaignId}`);

    // PASSO 2: Adicionar conteúdo simples e fixo
    const contentPayload = {
      subject: TEST_SUBJECT,
      from_name: 'Beatriz Rodrigues',
      from: 'luisfmaximo8@gmail.com',
      content_type: 'html',
      content: TEST_HTML_CONTENT
    };

    console.log(`A tentar adicionar conteúdo à campanha ${campaignId}...`);
    await axios.post(`https://connect.mailerlite.com/api/campaigns/${campaignId}/content`, contentPayload, { headers });
    console.log(`SUCESSO no PASSO 2! Conteúdo adicionado com sucesso!`);
    console.log('O TESTE FUNCIONOU!');

  } catch (error) {
    console.error('O TESTE FALHOU. Ocorreu um erro:');
    if (error.response) {
      console.error('Dados do Erro:', JSON.stringify(error.response.data, null, 2));
    } else {
      console.error('Mensagem de Erro:', error.message);
    }
    process.exit(1);
  }
}

runTest();