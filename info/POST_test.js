fetch("http://192.168.1.179:3055/set", {
  method: "POST",
  headers: {
    "Content-Type": "application/json;charset=utf-8",
  },
  body: JSON.stringify({ taskT: {max:25} }),
}).then(
  (response) => {
    console.log(response.text());
  },
  (error) => {
    console.log(error);
  },
);
