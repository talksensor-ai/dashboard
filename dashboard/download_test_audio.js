const https = require('https');
const fs = require('fs');

const url = 'https://pub-00c77c70f2f54813abf1578a369f0139.r2.dev/%D0%B0%D0%BA-%D0%BC%D0%B5%D1%87%D0%B5%D1%82%D1%8C/2026-05-21/tmplqbo4zti.wav';

https.get(url, (res) => {
  console.log('Status:', res.statusCode);
  console.log('Content-Type:', res.headers['content-type']);
  console.log('Content-Length:', res.headers['content-length']);
  console.log('Access-Control-Allow-Origin:', res.headers['access-control-allow-origin'] || 'NOT SET');
  
  const chunks = [];
  res.on('data', c => chunks.push(c));
  res.on('end', () => {
    const buf = Buffer.concat(chunks);
    console.log('\nFirst 44 bytes (WAV header):');
    console.log('RIFF:', buf.slice(0, 4).toString('ascii'));
    console.log('File size:', buf.readUInt32LE(4));
    console.log('WAVE:', buf.slice(8, 12).toString('ascii'));
    console.log('fmt :', buf.slice(12, 16).toString('ascii'));
    console.log('Audio format:', buf.readUInt16LE(20)); // 1 = PCM
    console.log('Channels:', buf.readUInt16LE(22));
    console.log('Sample rate:', buf.readUInt32LE(24));
    console.log('Bits per sample:', buf.readUInt16LE(34));
    console.log('Total bytes downloaded:', buf.length);
    
    // Save to temp for testing
    fs.writeFileSync('C:/Users/Aziz/.gemini/antigravity/brain/2374903e-05e1-4d3f-b247-a0ee3e55109c/scratch/test_audio.wav', buf);
    console.log('\nSaved to scratch/test_audio.wav');
  });
}).on('error', e => console.error('Error:', e.message));
