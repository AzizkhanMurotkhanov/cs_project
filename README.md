# Project "Reservation"
## Before
Make sure that you have [aiogram](https://pypi.org/project/aiogram) framework. Write your bot token in line 96 in project.py
## Beginning
After **/start** command, you will choose language you want, then you will have two choices: **customer** or **technician**.
## Customer side
If you are using it for the first time, you have to register: your **name**, **phone number** and **car type**. Then you will have several opitons in the selected language:
- List of services
- Get contact details
- Reservation details
- Cancel reservation
- Change my info
- Done
### List of services
You will choose service you need, then available date of reservation. It will be added to database, then you will be provided with options again.
### Get contact details
Contact details of every technician will be sent: his **name**, **phone number** and **telegram user**, then you will be provided with options again.
### Reservation details
Your reservation details will be provided, then you will be provided with options again.
### Cancel reservation
To cancel your reservation, if you want to do so. Then you will be provided with options again.
### Change my info
To change your **name**, **phone number** and **car type**. Then you will be provided with options again.
### Done
To end session.
## Technician side
If you are not in the database, you can't enter. If you are, you will have several opitons in the selected language:
- Take reservation
- List of available days
- Add technician
- Done
### Take reservation
You will be provived with available reservation and two options: **take** and **reject**. If **taken**, notification will be sent to the customer. If **rejected**, you will be provided with next reservation, if it exists. Then you will be provided with options again.
### List of available days
You will be provived with list of your free days and two options: **add** and **remove**. If **add** is chosen, you will be asked to input day of the '01.01.2020' form, but it also works with '01 jan 2020', '1/jan/20' or any other form. Then you will be asked to input time of the '12:00' form, but it also works with '12 00' or '12/00'. If **remove** is chosen, you will be asked to choose date you want to remove.
### Add technician
You will be asked to input new technician's **name**, phone **number**, telegram **user** and telegram **id** (for safety).
### Done
To end session.
## Admin side
It is easy to add new language. All you have to do is open **replies.json**, add new key next to 'English' and 'Русский', copy all the keys and translate their values (not key names).