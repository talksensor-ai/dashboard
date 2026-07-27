const { S3Client, PutBucketCorsCommand } = require('@aws-sdk/client-s3');

const client = new S3Client({
  region: 'auto',
  endpoint: 'https://8e3ec4a5155e2fa5ca84dc204bcd4546.r2.cloudflarestorage.com',
  credentials: {
    accessKeyId: '0a8f2d235d791ba77b0ae40fb5f71782',
    secretAccessKey: '7bda40fa9678239693b0356d8bb215f694c08bfe95bca41798959531d36aab4f',
  },
});

(async () => {
  try {
    const result = await client.send(new PutBucketCorsCommand({
      Bucket: 'kavabanga-audio',
      CORSConfiguration: {
        CORSRules: [
          {
            AllowedOrigins: ['*'],
            AllowedMethods: ['GET', 'HEAD'],
            AllowedHeaders: ['*'],
            MaxAgeSeconds: 86400,
          },
        ],
      },
    }));
    console.log('CORS set successfully:', result.$metadata.httpStatusCode);
  } catch (e) {
    console.error('Error setting CORS:', e.message);
  }
})();
