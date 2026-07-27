const https = require('https');

const urls = [
  'https://pub-00c77c70f2f54813abf1578a369f0139.r2.dev/ак-мечеть/2026-05-21/tmpcbs1dkr2.wav',
  'https://pub-00c77c70f2f54813abf1578a369f0139.r2.dev/ак-мечеть/2026-05-21/tmpem72o3i4.wav',
  'https://pub-00c77c70f2f54813abf1578a369f0139.r2.dev/ак-мечеть/2026-05-21/tmpc4uutrdb.wav',
  'https://pub-00c77c70f2f54813abf1578a369f0139.r2.dev/ак-мечеть/2026-05-21/tmplqbo4zti.wav',
  'https://pub-00c77c70f2f54813abf1578a369f0139.r2.dev/ак-мечеть/2026-05-21/tmpv30tix9m.wav'
];

function check(url) {
  return new Promise((resolve) => {
    https.request(encodeURI(url), { method: 'HEAD' }, (res) => {
      console.log(`URL: ${url}\nStatus: ${res.statusCode}\nContent-Length: ${res.headers['content-length']}\n`);
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
