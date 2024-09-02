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

variable "source_repository" {
  type        = string
  default     = "gear000/LudusSMA"
  description = "Source repository"
}

variable "source_branch" {
  type        = string
  default     = "main"
  description = "Source branch"
}

variable "parameters_file" {
  description = "Path to the JSON file containing SSM parameters."
  type        = string
  default     = "secrets.json"
}
