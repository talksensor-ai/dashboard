const {createClient} = require('@supabase/supabase-js');
const s = createClient(
  'https://itllqtmuvktatmpalzxo.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0bGxxdG11dmt0YXRtcGFsenhvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTI1ODY2NSwiZXhwIjoyMDk0ODM0NjY1fQ.LRVO8vAD-vOBmGI96JqIMkldk9eWDzqrXxlyTOkUIZQ'
);

(async () => {
  const {data: shops, error: se} = await s.from('shops').select('*');
  console.log('Shops:', shops);
  if (se) console.log('Shops error:', se);

  const {data: dialogs, error: de, count} = await s.from('dialogs').select('id, shop_id, score, created_at', {count: 'exact'});
  console.log('\nDialogs count:', count);
  if (dialogs) dialogs.forEach(d => console.log(`  id=${d.id} shop=${d.shop_id} score=${d.score} date=${d.created_at}`));
  if (de) console.log('Dialogs error:', de);

  const {data: tel} = await s.from('agent_telemetry').select('*');
  console.log('\nTelemetry:', tel);
})();
