const {createClient} = require('@supabase/supabase-js');
const s = createClient(
  'https://itllqtmuvktatmpalzxo.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0bGxxdG11dmt0YXRtcGFsenhvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTI1ODY2NSwiZXhwIjoyMDk0ODM0NjY1fQ.LRVO8vAD-vOBmGI96JqIMkldk9eWDzqrXxlyTOkUIZQ'
);

(async () => {
  const {data, error} = await s.from('dialogs')
    .select('id, dialog_index, created_at, audio_url, original_audio_file, clean_text, transcript')
    .eq('id', 111)
    .single();

  if (error) { console.error(error); return; }

  console.log('=== DIALOG ID 111 ===');
  console.log(`Index: ${data.dialog_index}`);
  console.log(`Original Audio File in DB: ${data.original_audio_file}`);
  console.log(`Audio URL: ${data.audio_url}`);
  console.log('Clean Text:', data.clean_text);
  console.log('Transcript Lines:');
  data.transcript.slice(0, 10).forEach(line => {
    console.log(`  [${line.start} - ${line.end}] ${line.speaker}: ${line.text}`);
  });
})();
