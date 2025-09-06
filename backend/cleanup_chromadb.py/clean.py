import chromadb

# Connexion à Chroma
client = chromadb.PersistentClient(path="db")

# Liste toutes les collections
collections = client.list_collections()
print("Collections existantes:", [c.name for c in collections])

# Supprimer chaque collection
for c in collections:
    client.delete_collection(c.name)

print("✅ Toutes les collections ont été supprimées")
