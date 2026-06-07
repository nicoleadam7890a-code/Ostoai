# Send Appointment to Doctor

To actually send the appointment to the doctor, we need to connect your frontend form to the backend (`api.py`). I recommend a two-step approach for maximum reliability:

1. **Save to Database (MongoDB):** Store the appointment details in a new `appointments` collection in your existing MongoDB Atlas database. This allows doctors to log in and view a dashboard of all appointments.
2. **Send an Email Notification:** Use Python's built-in `smtplib` to automatically send an email to the doctor's email address containing the patient's details as soon as the appointment is booked.

## Proposed Changes

### Backend API (`api.py`)
#### [MODIFY] api.py
- Add an `appointments_collection = db.appointments` reference.
- Create a new POST route `@app.route('/book_appointment', methods=['POST'])`.
- In the route, save the incoming appointment data (Name, Email, Phone, Specialist, Date, Time, Notes) to the `appointments_collection`.
- (Optional) Use `smtplib` to send an email to a designated doctor email address (you will need to provide an email and an App Password in your `.env` file).

### Frontend Form (`doctor_appoint.html`)
#### [MODIFY] doctor_appoint.html
- Replace the simulated `setTimeout` in the form submission with an actual `fetch('/book_appointment')` call.
- Pass the form data (Name, Email, Phone, Specialist, Date, Time, Notes) as JSON to the backend.

## Open Questions

> [!IMPORTANT]
> 1. **Do you just want to save it to the MongoDB database**, or **do you also want an email sent to the doctor?**
> 2. If you want emails sent, you will need a Gmail account and an "App Password" to allow your Python script to send emails safely. Are you okay with setting this up?

Let me know how you'd prefer to proceed, and I will write the code!
