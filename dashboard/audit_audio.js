const {createClient} = require('@supabase/supabase-js');
const s = createClient(
  'https://itllqtmuvktatmpalzxo.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0bGxxdG11dmt0YXRtcGFsenhvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTI1ODY2NSwiZXhwIjoyMDk0ODM0NjY1fQ.LRVO8vAD-vOBmGI96JqIMkldk9eWDzqrXxlyTOkUIZQ'
);

(async () => {
  const {data, error} = await s.from('dialogs')
    .select('id, dialog_index, created_at, audio_url, original_audio_file, transcript')
    .order('created_at', {ascending: true});

  if (error) { console.error(error); return; }

  console.log(`Total dialogues: ${data.length}\n`);
  
  let noAudio = 0;
  let hasAudio = 0;
  let mismatch = 0;

  data.forEach(d => {
    const hasUrl = d.audio_url && d.audio_url.length > 5;
    if (hasUrl) hasAudio++; else noAudio++;
    
    // Check if transcript timestamps make sense with the audio
    const firstLine = d.transcript && d.transcript[0];
    const lastLine = d.transcript && d.transcript[d.transcript.length - 1];
    const dialogStart = firstLine ? firstLine.start : null;
    const dialogEnd = lastLine ? lastLine.end : null;
    const durationSec = (dialogStart !== null && dialogEnd !== null) ? (dialogEnd - dialogStart) : null;
    
    // Check created_at time vs transcript start time
    const createdHour = d.created_at ? new Date(d.created_at).getUTCHours() : null;
    const transcriptHour = dialogStart !== null ? Math.floor(dialogStart / 3600) : null;
    
    const hourMatch = (createdHour !== null && transcriptHour !== null) ? (createdHour === transcriptHour) : null;

    console.log(`ID:${d.id} idx:${d.dialog_index} time:${d.created_at} audio:${hasUrl ? 'YES' : 'NO'} file:${d.original_audio_file || 'none'} transcript_start:${dialogStart}s transcript_end:${dialogEnd}s duration:${durationSec ? durationSec.toFixed(0) + 's' : 'N/A'} hour_match:${hourMatch}`);
  });

  console.log(`\n--- Summary ---`);
  console.log(`Has audio URL: ${hasAudio}`);
  console.log(`Missing audio URL: ${noAudio}`);
})();
