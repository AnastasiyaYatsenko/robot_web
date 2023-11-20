function ajaxsubmit({form='', query=''} = {})
{
  var data = $('#'+form).serialize();
  if (query) {
    if (data) { data = data + '&'; }
    data = data + query;
  }
//  alert(data);
  $.ajax({
    type: "POST",
    url: "/",
    data: data
  });
}