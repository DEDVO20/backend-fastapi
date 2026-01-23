#!/bin/bash
# Script para inicializar y poblar la base de datos

echo "🔄 Esperando a que PostgreSQL esté listo..."
sleep 5

echo "🔨 Creando tablas en la base de datos..."
python -m app.db.init_db

echo "🌱 Insertando datos iniciales..."
python -m app.db.seed_data

echo "✅ Inicialización completada!"
