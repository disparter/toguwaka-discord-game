#!/bin/bash

S3_BUCKET="tokugawa-db-storage"
LOCAL_DB="data/tokugawa.db"

if [ -f "$LOCAL_DB" ]; then
    aws s3 cp "$LOCAL_DB" "s3://$S3_BUCKET/tokugawa.db" && echo "Upload para S3 concluído com sucesso!" || echo "Erro ao fazer upload para S3."
else
    echo "Banco de dados não encontrado: $LOCAL_DB"
fi