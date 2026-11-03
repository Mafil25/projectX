const error = document.querySelector(".content_error")
const inputs = document.querySelectorAll("main .info input")


if (error.textContent !== "") {
  inputs.forEach((input) => {
    input.classList.add("err")
  })
}