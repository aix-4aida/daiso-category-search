module.exports = {
  apps: [
    {
      name: 'daiso-api',
      cwd: './backend',
      script: 'uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000',
      interpreter: 'python',
      interpreter_args: '-m',
      env: {
        APP_ENV: 'production',
      },
      max_memory_restart: '256M',
    },
    {
      name: 'daiso-qdrant',
      script: './qdrant',
      args: '--storage-path ./qdrant_data',
      cwd: '/opt/qdrant',
      max_memory_restart: '128M',
    },
  ],
};
