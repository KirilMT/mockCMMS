// Initialization function
function initAdvancedTable(containerId, data, columns, pageSize = 25) {


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



    return table;
}

let advTable;