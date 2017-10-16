<img src="https://avatars3.githubusercontent.com/u/21263910?v=3&s=100" alt="MoarCatz logo"
     title="MoarCatz" align="right" />

# Timetable Server
Server side of the SESC timetable application.  
Responsible for collecting data and sending it out via push notifications as well as supporting the **Vacant Rooms** and **Session Pics** services.

## Dependencies
* [odfpy](https://github.com/eea/odfpy)
* [Requests](https://github.com/requests/requests)
* [HTTMock](https://github.com/patrys/httmock)
* [psycopg2](https://github.com/psycopg/psycopg2)

## Data Updating
Server collects data at different intervals, depending on the update frequency.

* Permanent timetable for the week for every class  
  Update: 1 day
* Rings timetable  
  Update: once on 1st Sep
* Teachers  
  Update: 1 month
    * Classes that have lessons with this teacher  
    Update: 1 day
    * Teacher's timetable  
      Update: 1 day
* Changes  
  Update: 15 minutes
* Vacant rooms  
  Update: 1 day (except for Sundays)
* Study plan  
  Update: every week in Sep, once on 1st Oct
* Class's teachers  
  Update: 1 month
* Classes  
  Update: once on 1st Sep

## License
This project is licensed under the GPL-3.0 License - see the [LICENSE](https://github.com/MoarCatz/timetable-server/blob/master/LICENSE) file for details.

## Any Questions?
Shoot us a mail at timetable@alexfox.co. We will be happy to meet you :sparkles:
