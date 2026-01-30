fetch("http://192.168.1.132:3055/set", {
  method: "POST",
  headers: {
    "Content-Type": "application/json;charset=utf-8",
  },
  body: JSON.stringify({ heater: 0 }),
}).then(
  (response) => {
    console.log(response.json());
  },
  (error) => {
    console.log(error);
  },
);
