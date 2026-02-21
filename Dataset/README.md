# 📁 Datasets & Generation Scripts

This repository includes a dedicated folder containing all the data required to run and test the application. 
The folder contains the raw starting data before processing, the processed data (perfectly formatted and ready to be imported into MongoDB and Neo4j), and the scripts and code used to generate relationships, reviews, and data iterations.

---

## ⚠️ Important Note for MongoDB Import

All final datasets are ready for a direct import. However, after importing the `reviews.csv` file into MongoDB, the `review_date` field will initially be stored as a `String`.
To ensure the Analytics (like the "Glow Up" feature) work correctly, you must manually convert these strings into proper `Date` objects. 
Run the following command in your MongoDB shell (or via MongoDB Compass) immediately after the import:

```javascript
db.reviews.updateMany(
   { review_date: { $type: "string" } },
   [{ $set: { review_date: { $toDate: "$review_date" } } }]
)
```

---

## 🔐 Test Credentials

For security reasons, all user and admin passwords are encrypted in the database using the **BCrypt** hashing algorithm. 
To easily navigate, explore the platform, and test the REST APIs, you can log in using the following cleartext credentials:

### Administrator Account
* **Email:** `admin@largescale.it`
* **Password:** `Admin123!`

### User Accounts
* **Email:** `user1@largescale.it`
* **Password:** `KNERMPyQUe`

* **Email:** `user2@largescale.it`
* **Password:** `G2HEj2HccI`

* **Email:** `user224@largescale.it`
* **Password:** `2YQGKKexxO`

* **Email:** `user11694@largescale.it`
* **Password:** `VBVdPBAVJu`
