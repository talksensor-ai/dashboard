const {createClient} = require('@supabase/supabase-js');
const s = createClient(
  'https://itllqtmuvktatmpalzxo.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0bGxxdG11dmt0YXRtcGFsenhvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTI1ODY2NSwiZXhwIjoyMDk0ODM0NjY1fQ.LRVO8vAD-vOBmGI96JqIMkldk9eWDzqrXxlyTOkUIZQ'
);

(async () => {
  const {data, error} = await s.from('dialogs')
    .select('id, dialog_index, created_at, audio_url, original_audio_file, clean_text')
    .order('created_at', {ascending: true});

  if (error) { console.error(error); return; }

  console.log('=== Dialogs WITHOUT audio ===\n');
  data.filter(d => !d.audio_url || d.audio_url.length < 5).forEach(d => {
    console.log(`ID:${d.id} idx:${d.dialog_index} time:${d.created_at} file:${d.original_audio_file}`);
    console.log(`  text: ${(d.clean_text || '').substring(0, 120)}...\n`);
  });

  // Also check for duplicated audio URLs (same file mapped to different dialogs)
  const urlMap = {};
  data.forEach(d => {
    if (d.audio_url && d.audio_url.length > 5) {
      if (!urlMap[d.audio_url]) urlMap[d.audio_url] = [];
      urlMap[d.audio_url].push(d.id);
    }
  });
  
  const dupes = Object.entries(urlMap).filter(([_, ids]) => ids.length > 1);
  if (dupes.length > 0) {
    console.log('\n=== DUPLICATED audio URLs (same file on multiple dialogs) ===\n');
    dupes.forEach(([url, ids]) => {
      console.log(`URL: ${url}\n  Used by dialog IDs: ${ids.join(', ')}\n`);
    });
  } else {
    console.log('\nNo duplicated audio URLs found - each dialog has unique audio.');
  }

  // Check if any audio_url files return wrong content-length (too small)
  console.log('\n=== Audio file sizes distribution ===');
  const sizes = data.filter(d => d.audio_url).map(d => d.audio_url);
  console.log(`Total unique audio URLs: ${new Set(sizes).size}`);
})();
