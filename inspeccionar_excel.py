#!/usr/bin/env python
"""
Script para inspeccionar el archivo Excel y ver las columnas disponibles
"""

import pandas as pd
import sys

def inspeccionar_excel():
    """Inspecciona el archivo Excel"""
    try:
        # Leer el archivo Excel
        df = pd.read_excel('Lista empleados.xls')
        
        print("🔍 INSPECCIÓN DEL ARCHIVO EXCEL")
        print("=" * 60)
        print(f"📊 Total de filas: {len(df)}")
        print(f"📋 Total de columnas: {len(df.columns)}")
        
        print("\n📑 COLUMNAS DISPONIBLES:")
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. '{col}'")
        
        print("\n📋 PRIMERAS 5 FILAS:")
        print(df.head().to_string())
        
        print("\n🔍 INFORMACIÓN DE COLUMNAS:")
        print(df.info())
        
        print("\n📊 VALORES ÚNICOS EN PRIMERAS COLUMNAS:")
        for col in df.columns[:5]:
            valores_no_nulos = df[col].dropna().nunique()
            print(f"- {col}: {valores_no_nulos} valores únicos")
        
        # Buscar posibles columnas de documento
        print("\n🔎 BUSCANDO COLUMNAS DE DOCUMENTO:")
        doc_columns = [col for col in df.columns if 'doc' in col.lower() or 'dni' in col.lower()]
        if doc_columns:
            for col in doc_columns:
                print(f"- Posible columna documento: '{col}'")
                print(f"  Primeros valores: {df[col].dropna().head(3).tolist()}")
        
        # Buscar posibles columnas de nombre
        print("\n👤 BUSCANDO COLUMNAS DE NOMBRE:")
        name_columns = [col for col in df.columns if 'nom' in col.lower() or 'apell' in col.lower()]
        if name_columns:
            for col in name_columns:
                print(f"- Posible columna nombre: '{col}'")
                print(f"  Primeros valores: {df[col].dropna().head(3).tolist()}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error al leer el archivo Excel: {e}")
        return None

if __name__ == "__main__":
    inspeccionar_excel()
