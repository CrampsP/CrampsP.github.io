View(infert)
?infert
infert.glm <- glm( (spontaneous > 0) ~ age, data=infert, family=binomial)
b <- coef(infert.glm)
b
summary(infert.glm)
plot( (spontaneous > 0) ~ age, data=infert)
curve( exp(b[1] + b[2]*x)/(1 + exp(b[1] + b[2]*x)), add=TRUE)
table(infert$age)
install.packages("ResourceSelection")
library(ResourceSelection)
hoslem.test(infert$age, fitted(infert.glm))
pchisq(334.01, df = 246, lower.tail=FALSE)


model <- glm(sex ~ height, data = Galton, family = binomial)
summary(model)
b <- coef(model)
b

predict(model,  newdata = data.frame(height = 65), type = "response")
?predict

pchisq(626.22, 896, lower.tail=FALSE)
hoslem.test(model$y, model$fitted, g=10)

