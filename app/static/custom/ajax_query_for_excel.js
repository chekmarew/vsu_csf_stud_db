$(document).ready(function () {

    $("#print-to-excel").click(function () {
        var excel_data;

        var table = $(".table");

        $.ajax({
            method: "GET",
            url: "/excel_attendance",
            data: {
                excel_data: excel_data
            }
        })
    });

});