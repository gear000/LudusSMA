locals {
  parameters = jsondecode(file(var.parameters_file))
}
