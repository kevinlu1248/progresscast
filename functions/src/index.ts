import * as functions from "firebase-functions";
import admin from "firebase-admin";

import express from "express";
import cors from "cors";
import randomstring from "randomstring";
import generator from "project-name-generator";

admin.initializeApp({
  credential: admin.credential.applicationDefault(),
  databaseURL: "https://progresscast-default-rtdb.firebaseio.com",
});
const db = admin.database();

const app = express();
app.use(cors({ origin: true }));

enum Status {
  not_started = "not started",
  in_progress = "in progress",
  completed = "completed",
  error = "error",
  disconnected_or_crashed = "disconnected or crashed",
}

interface Loadbar {
  current: number;
  total: number;
  status: Status;
}

interface Session {
  // to be stored in database
  // user: string;
  slug: string;
  apiKey: string;
  loadbar: Loadbar;
  log: string;
}

// const color_from_status: {[key: string]: string} = {
//   not_started: "white",
//   in_progress: "blue",
//   completed: "green",
//   error: "red",
//   disconnected_or_crashed: "black"
// }

app.post("/getKey", (request, response) => {
  if (!request.body.total) {
    response.status(400).send("Request requires 'total' peramater.");
    return;
  }
  const apiKey = randomstring.generate({ length: 32 });
  const slug: string = generator({ words: 3, number: true }).dashed; // TODO: check that this is unique

  const responseSession: Session = {
    slug: slug,
    apiKey: apiKey,
    loadbar: {
      current: request.body.current || 0,
      total: request.body.total,
      status: request.body.current ? Status.in_progress : Status.not_started,
    },
    log: request.body.log || "",
  };
  db.ref(`sessions/${slug}`)
    .set(responseSession)
    .then((res) => {
      console.log(`response from db: ${res}`);
      response.json(responseSession);
    })
    .catch((err) => {
      console.error(err);
      response.status(400).send(`Error sending to database with ${err}`);
    });
});
exports.api = functions.https.onRequest(app);

app.post("/update", (request, response) => {
  // updates status, current and total and appends log
  if (!request.body.slug) {
    response.status(400).send("Need slug");
    return;
  }
  if (!request.body.apiKey) {
    response.status(400).send("Need API Key");
    return;
  }
  db.ref(`sessions/${request.body.slug}`)
    .get()
    .then((sessionSnapshot) => {
      if (request.body.apiKey != sessionSnapshot.val()["apiKey"]) {
        response.status(400).send("Error: API Key does not match our records");
      }
      const updateObj = request.body;
      delete updateObj.slug;
      delete updateObj.apiKey;
      if (request.body.log) {
        updateObj.log = sessionSnapshot.val()["log"].concat(request.body.log);
      }
      db.ref(`sessions/${request.body.slug}`)
        .update(updateObj)
        .then((res) => {
          response.status(200).end();
        })
        .catch((err) => {
          console.error(err);
          response.status(400).send(`Error database retrieval error (${err}`);
        });
    })
    .catch((err) => {
      console.error(err);
      response.status(400).send(`Error database retrieval error (${err}`);
    });
});

/*
Calls:
- get password
- set state (current, total, status) (requires muid and password)
- append log (also required muid and apikey)

verifying apikey

Each object in database: {
  loadbar: {

  }
}
sessions
*/
