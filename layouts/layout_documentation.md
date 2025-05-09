# Screen Layout Documentation

**Layout loading**
-

For a layout too be loaded it has to be placed inside the layouts directory and named with ```.html``` as file ending.

**Layout Format**
-

As indicated by the enforced ```.html``` file ending the layouts use HTML5 as format.
The conntent of the layout file will be set as the inner HTML conntent of the ```<body>``` Tag.
Additinaly all Tags with bredifined ids will have there inner HTML content set with Data according to the Screen settings.

Following is a set of ids and the Data there Tags will be filled with.

|ID                 |DATA                                                                                                           |
|-------------------|---------------------------------------------------------------------------------------------------------------|
|event_name         |Name of the current Event at Screen location                                                                   |
|event_desc         |Description of the current Event at Screen location                                                            |
|event_next         |Predefined HTML with Info of the next Event at Screen location                                                  |
