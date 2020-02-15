
def error_message(err):
	template = "An exception of type {0} occurred. Arguments:\n{1!r}"
	message = template.format(type(err).__name__, err.args)
	return message