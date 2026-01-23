"""
Script de debugging para identificar el problema del login
"""
from app.database import SessionLocal
from app.models.usuario import Usuario
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def debug_login():
    db = SessionLocal()
    
    try:
        # Buscar usuario admin
        usuario = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
        
        if not usuario:
            print("❌ Usuario admin NO existe en la base de datos")
            return
        
        print("✅ Usuario admin encontrado")
        print(f"   - Nombre: {usuario.nombre}")
        print(f"   - Email: {usuario.correo_electronico}")
        print(f"   - Activo: {usuario.activo}")
        print(f"   - Hash almacenado: {usuario.contrasena_hash[:50]}...")
        
        # Probar diferentes passwords
        passwords_a_probar = ["admin123", "admin", "password123"]
        
        print("\n🔍 Probando verificación de passwords:")
        for pwd in passwords_a_probar:
            try:
                resultado = pwd_context.verify(pwd, usuario.contrasena_hash)
                print(f"   - '{pwd}': {'✅ CORRECTO' if resultado else '❌ INCORRECTO'}")
            except Exception as e:
                print(f"   - '{pwd}': ❌ ERROR: {str(e)}")
        
        # Generar nuevo hash y comparar
        print("\n🔧 Generando nuevo hash para 'admin123':")
        nuevo_hash = pwd_context.hash("admin123")
        print(f"   Hash generado: {nuevo_hash[:50]}...")
        
        # Verificar el nuevo hash
        verif = pwd_context.verify("admin123", nuevo_hash)
        print(f"   Verificación del nuevo hash: {'✅ FUNCIONA' if verif else '❌ NO FUNCIONA'}")
        
        # Actualizar usuario con nuevo hash
        print("\n🔄 Actualizando usuario con nuevo hash...")
        usuario.contrasena_hash = nuevo_hash
        db.commit()
        print("✅ Usuario actualizado")
        
        # Verificar nuevamente
        db.refresh(usuario)
        verif_final = pwd_context.verify("admin123", usuario.contrasena_hash)
        print(f"   Verificación final: {'✅ FUNCIONA' if verif_final else '❌ NO FUNCIONA'}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_login()
