// firebase.js

// Import Firebase modules
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

// Your Firebase config (replace with your actual values)
const firebaseConfig = {
  apiKey: "AIzaSyAPwplgr5ap8QRlF1h-k8lUCgGNyUb5Pxk",
  authDomain: "bd-fitness-challenge-2026.firebaseapp.com",
  projectId: "bd-fitness-challenge-2026",
  storageBucket: "bd-fitness-challenge-2026.appspot.com",
  messagingSenderId: "447583093963",
  appId: "1:447583093963:web:c4d49a03db329f4090474e",
  measurementId: "G-8MM6TDDVXX"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firestore
const db = getFirestore(app);

// Export db for use in other files
export { db };