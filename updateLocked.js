const admin = require("firebase-admin");
const serviceAccount = require("./firebase_key.json"); // Asegúrate de que la ruta sea correcta

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  projectId: "identityverifierapp"
});

const db = admin.firestore();

async function updateField() {
  try {
    await db.collection("cronLocks").doc("taskLock").update({
      locked: false
    });
    console.log("✅ Campo 'locked' actualizado a false.");
  } catch (err) {
    console.error("❌ Error actualizando:", err.message);
  }
}

updateField();