library(cars)
View(mtcars)
palette(c("grey", "skyblue", "blue", "red"))
plot(mpg ~ qsec, data = mtcars, col = as.factor(am), pch = 16, xlim = c(13, 24), ylim = (c(8, 38)))
legend("topright", col=palette(), legend=c("Automatic", "Manual"), bty = "y", text.col = palette())
carlm <- lm(mpg ~ qsec + am + qsec:am, data = mtcars)
summary(carlm)
plot(carlm)

b <- coef(carlm)
b

curve(b[1] + b[2]*x, col = "grey", add = TRUE)
curve((b[1]+b[3]) + (b[2]+b[4])*x, col = "skyblue", add = TRUE)

b[1]
b[2]
b[1]+b[3]
b[2]+b[4]
