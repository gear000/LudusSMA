variable "aws_region" {
  type        = string
  default     = "eu-west-1"
  description = "AWS Region"
}

variable "tags" {
  type = map(any)
  default = {
    "projectID" = "LudusSMA"
    "rg"        = "foundation"
  }
  description = "Tags"
}
