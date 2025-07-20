const axios = require('axios');
const API_KEY = process.env.MAILERLITE_API_KEY;
const GROUP_ID = '160388108749112929';
const NEWSLETTER_SUBJECT = process.env.NEWSLETTER_SUBJECT;
const NEWSLETTER_MESSAGE = process.env.NEWSLETTER_MESSAGE;

if (!API_KEY || !GROUP_ID || !NEWSLETTER_SUBJECT || !NEWSLETTER_MESSAGE) {
  console.error('Erro: Uma ou mais variáveis de ambiente estão em falta.');
  process.exit(1);
}

const emailHtmlContent = `
  <h1>Novidades no Portfólio de Beatriz Rodrigues</h1>
  <p>${NEWSLETTER_MESSAGE}</p>
  <p>Venha ver as últimas novidades no site!</p>
  <a
    href="https://manmaxim0.github.io/Bia/"
    style="background-color: #0056b3; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;"
  >
    Visitar o Site
  </a>
  <p style="font-size: 12px; color: #888; margin-top: 20px;">
    Recebeu este e-mail porque subscreveu a nossa newsletter.
  </p>
`;

async function sendNewsletter() {
  console.log('A preparar para enviar a newsletter...');
  try {
    const response = await axios.post('https://connect.mailerlite.com/api/campaigns', {
      name: `Newsletter - ${new Date().toLocaleDateString('pt-PT')}`,
      type: 'regular',
      emails: [{
        subject: NEWSLETTER_SUBJECT,
        from_name: 'Beatriz Rodrigues',
        from: 'luisfmaximo8@gmail.com',
        content_type: 'html',
        content: emailHtmlContent
      }],
      groups: [GROUP_ID]
    }, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    console.log('Campanha criada com sucesso! ID:', response.data.data.id);
    console.log('O MailerLite irá começar o envio em breve.');
  } catch (error) {
    console.error('Ocorreu um erro ao comunicar com a API do MailerLite:');
    if (error.response) {
      console.error(error.response.data);
    } else {
      console.error(error.message);
    }
    process.exit(1);
  }
}

sendNewsletter();