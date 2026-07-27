const {createClient} = require('@supabase/supabase-js');
const s = createClient(
  'https://itllqtmuvktatmpalzxo.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0bGxxdG11dmt0YXRtcGFsenhvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTI1ODY2NSwiZXhwIjoyMDk0ODM0NjY1fQ.LRVO8vAD-vOBmGI96JqIMkldk9eWDzqrXxlyTOkUIZQ'
);

(async () => {
  const {data: dialogs, error: de} = await s.from('dialogs').select('id, created_at, audit_details');
  if (de) {
    console.error('Error fetching dialogs:', de);
    return;
  }

  const types = {};
  console.log('Total dialogs:', dialogs.length);
  dialogs.forEach(d => {
    const type = d.audit_details ? d.audit_details.dialogue_type : 'null';
    types[type] = (types[type] || 0) + 1;
    if (d.created_at.startsWith('2026-05-21')) {
      console.log(`  id=${d.id} type=${type} date=${d.created_at} score=${d.audit_details ? d.audit_details.score : 'none'}`);
    }
  });
  console.log('\nDialogue Types Summary:', types);
})();
