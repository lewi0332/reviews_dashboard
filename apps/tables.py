from dash.dash_table import FormatTemplate as FormatTemplate


defaultColDef = {
#  "filter": "agNumberColumnFilter",
"enableCellTxtSelection": True,
"ensureDomOrder": True,
 "resizable": True,
 "sortable": True,
 "editable": False,
 "floatingFilter": True,
}

columnDefs = [
    {'headerName': 'Date', 'field': 'order_date', 'type': 'dateColumn', 'filter': 'agDateColumnFilter', 'filterParams': {'comparator': 'equals', 'browserDatePicker': True}, 'valueFormatter': 'data.value ? new Date(data.value).toLocaleDateString() : ""'},
    {'headerName': 'Food Item', 'field': 'item_id'},
    {'headerName': 'Rating', 'field': 'item_rating', 'filter':True},
    {'headerName': 'Comment', 'field': 'consumer_comment', 'width': 500},   
 ]