// Initialization function
function initAdvancedTable(containerId, data, columns, pageSize = 25) {
    console.log('initAdvancedTable called with:', containerId, 'data items:', data?.length);

    let container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with ID '${containerId}' not found`);
        return null;
    }

    const table = new AdvancedTable(containerId, {
        data: data,
        columns: columns,
        pageName: containerId,
        pageSize: pageSize
    });

    window.advTable = table;

    if (typeof advTable === 'undefined') {
        window.advTable = table;
    }

    console.log('Advanced table initialized, window.advTable is:', window.advTable);

    return table;
}

let advTable;