{% for t in site.data.conferences %}

{{ forloop.rindex  }} {{ t.name }} 
* {{ t.conf }} 
* {{ t.loc }} 
* {{ t.date }}   

--- 
{% endfor %}

