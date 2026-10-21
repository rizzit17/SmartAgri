"""Isolated UI regression checks: python -m unittest discover -s tests."""
import json
import os
import pickle
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest
import streamlit as st
from sklearn.ensemble import RandomForestClassifier

APP = Path(__file__).resolve().parents[1] / "dashboard.py"


class DashboardTests(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()
        st.cache_resource.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        os.environ["SMARTAGRI_DATA_DIR"] = self.temp.name
        self.app = AppTest.from_file(str(APP), default_timeout=20).run()

    def tearDown(self):
        self.temp.cleanup()
        os.environ.pop("SMARTAGRI_DATA_DIR", None)

    def signup(self):
        self.app.radio[0].set_value("Create account").run()
        for field, value in zip(self.app.text_input, ["gardener", "greenfield123", "greenfield123"]):
            field.set_value(value)
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertTrue(self.app.session_state["logged_in"])

    def page(self, name):
        self.app.radio[0].set_value(name).run()
        self.assertFalse(self.app.exception)

    def test_empty_screens_and_auth(self):
        self.app.button[0].click().run()
        self.assertTrue(self.app.error)
        self.signup()
        users = json.loads((self.root / "users.json").read_text())
        self.assertTrue(users["gardener"]["password_hash"].startswith("pbkdf2_sha256$"))
        for name in ["History", "Crops", "Field notes", "Reports", "Account"]:
            self.page(name)
        next(b for b in self.app.button if b.label == "Sign out").click().run()
        self.assertEqual(self.app.radio[0].value, "Sign in")
        self.app.text_input[0].set_value("gardener")
        self.app.text_input[1].set_value("wrong")
        self.app.button[0].click().run()
        self.assertTrue(self.app.error)
        self.app.text_input[1].set_value("greenfield123")
        self.app.button[0].click().run()
        self.assertTrue(self.app.session_state["logged_in"])

    def test_live_pages_report_chat_and_password(self):
        (self.root / "latest.json").write_text(json.dumps({"temperature": 27, "humidity": 60, "moisture": 0, "outside_temp": 26, "wind_speed": 15, "city": "Vellore"}))
        (self.root / "sensor_log.csv").write_text("timestamp,soil_temp,humidity,soil_moisture\n2026-10-18 10:00:00,26,60,40\n2026-10-19 10:00:00,27,60,0\n")
        model = RandomForestClassifier(n_estimators=3, random_state=1).fit([[20,50,20],[27,60,40],[30,70,60]], ["rice","maize","cotton"])
        (self.root / "crop_model.pkl").write_bytes(pickle.dumps(model))
        self.signup()
        self.assertEqual(self.app.metric[2].value, "0.0 %")
        self.assertTrue(self.app.error)
        for name in ["History", "Crops", "Field notes"]:
            self.page(name)
        next(b for b in self.app.button if b.label == "Check moisture").click().run()
        self.assertEqual(len(self.app.chat_message), 2)
        self.page("Reports")
        next(b for b in self.app.button if b.label == "Prepare snapshot").click().run()
        self.assertTrue(self.app.session_state["report_pdf"].startswith(b"%PDF"))
        self.app.run()
        self.assertTrue(self.app.session_state["report_pdf"])
        self.page("Account")
        for field, value in zip(self.app.text_input, ["greenfield123", "newpassword123", "newpassword123"]):
            field.set_value(value)
        next(b for b in self.app.button if b.label == "Update password").click().run()
        self.assertTrue(self.app.success)

    def test_legacy_login_migrates(self):
        (self.root / "users.json").write_text(json.dumps({"legacy": "oldpassword"}))
        self.app.text_input[0].set_value("legacy")
        self.app.text_input[1].set_value("oldpassword")
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertIn("password_hash", json.loads((self.root / "users.json").read_text())["legacy"])


if __name__ == "__main__":
    unittest.main()
