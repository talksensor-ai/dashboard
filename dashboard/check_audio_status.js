const https = require('https');

const urls = [
  'https://pub-00c77c70f2f54813abf1578a369f0139.r2.dev/ак-мечеть/2026-05-21/tmpcbs1dkr2.wav',
  'https://pub-00c77c70f2f54813abf1578a369f0139.r2.dev/%D0%B0%D0%BA-%D0%BC%D0%B5%D1%87%D0%B5%D1%82%D1%8C/2026-05-21/tmpcbs1dkr2.wav',
  'https://pub-00c77c70f2f54813abf1578a369f0139.r2.dev/-/2026-05-21/tmpcbs1dkr2.wav'
];

function check(url) {
  return new Promise((resolve) => {
    https.request(url, { method: 'HEAD' }, (res) => {
      console.log(`URL: ${url}\nStatus: ${res.statusCode}\nHeaders: ${JSON.stringify(res.headers)}\n`);
      resolve();
    }).on('error', (e) => {
      console.error(`URL: ${url}\nError: ${e.message}\n`);
      resolve();
    }).end();
  });
}

(async () => {
  for (const url of urls) {
    await check(url);
  }
})();
