$(document).ready(function(){
    if ($("#phone").length > 0)
    {
        var input_phone = $("#phone");
        input_phone.attr("type", "text");
        input_phone.removeAttr("min");
        input_phone.removeAttr("max");
        input_phone.mask("+7(900)000-00-00",{placeholder:"*"});

        var f = $(input_phone[0].form);
        f.submit(function(){
            var p = input_phone.val();
            p = p.replace(/[\+,\-,\(,\)]/g, "");
            input_phone.val(p);
        });
    }
});