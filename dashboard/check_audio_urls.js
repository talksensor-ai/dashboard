const {createClient} = require('@supabase/supabase-js');
const s = createClient(
  'https://itllqtmuvktatmpalzxo.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0bGxxdG11dmt0YXRtcGFsenhvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTI1ODY2NSwiZXhwIjoyMDk0ODM0NjY1fQ.LRVO8vAD-vOBmGI96JqIMkldk9eWDzqrXxlyTOkUIZQ'
);

(async () => {
  const {data: dialogs, error} = await s.from('dialogs')
    .select('id, audio_url, created_at')
    .order('created_at', {ascending: false})
    .limit(10);

  if (error) {
    console.error('Error:', error);
    return;
  }

  console.log('Recent Dialogues Audio URLs:');
  dialogs.forEach(d => {
    console.log(`ID: ${d.id}, Date: ${d.created_at}, URL: ${d.audio_url}`);
  });
})();
