# Screen Layout Documentation

**Layout loading**
-

For a layout to be loaded it has to be placed inside the layouts directory and named with ```.html``` as file ending.

**Layout Format**
-

As indicated by the enforced ```.html``` file ending the layouts use HTML5 as format.
The content of the layout file will be set as the inner HTML content of the ```<body>``` Tag.
Additionally, all Tags with predefined ids will have their inner HTML content set with Data according to the Screen settings.

Following is a set of ids and the Data there Tags will be filled with.

| ID               | DATA                                                    |
|------------------|---------------------------------------------------------|
| event_name       | Name of the current Event at Screen location            |
| event_desc       | Description of the current Event at Screen location     |
| event_start      | Starting Time of the current Event at Screen location   |
| event_len        | Length in min of the current Event at Screen location   |
| event_next_name  | Name of the next Event at Screen location               |
| event_next_desc  | Description of the next Event at Screen location        |
| event_next_start | Starting Time of the next Event at Screen location      |
| event_next_len   | Length in min of the next Event at Screen location      |
| location         | Location of the Screen without prefix (regex="^\\[.*]") |
| msg_of_the_day   | Message of the Day, as set in Admin panel               |
