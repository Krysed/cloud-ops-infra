## DevOps infrastructure project.

Purpose of this project is not to build amazing web aplication, but rather to get more hands on approach on infrastructure and automation.

The web template that is used fot this project was found on [tooplate.com](https://www.tooplate.com). 
Link to the resource zip: [link](https://www.tooplate.com/zip-templates/2136_kool_form_pack.zip)

There is a setup script `setup.sh` that will install every single tool needed to interact with the project environment.

## Environment Configuration

This project uses environment variables for configuration. Copy `.env.example` to `.env` and set your values:

```bash
cp .env.example .env
```

Required environment variables:
- `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`
- `REDIS_HOST`, `REDIS_PASSWORD`, `REDIS_PORT`, `REDIS_DB`
- `ENV` (set to `dev` for development)
