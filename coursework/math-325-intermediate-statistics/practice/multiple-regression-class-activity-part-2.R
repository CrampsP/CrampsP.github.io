palette(c("skyblue","firebrick"))

plot(mpg ~ qsec, data=mtcars, col=as.factor(am), xlim=c(0,30), ylim=c(-30,40), main="1974 Motor Trend Cars", pch=16)

someNameForYourLM <- lm(mpg ~ qsec + am, data=mtcars)

summary(someNameForYourLM)

b <- coef(someNameForYourLM)
b

abline(b[1], b[2], col=palette()[1])

abline((b[1]+b[3]), (b[2]), col=palette()[2])

legend("topleft", legend=c("automatic","manual"), pch=1, col=palette(), title="Transmission (am)", bty="n")








palette(c("skyblue","firebrick"))

plot(mpg ~ qsec, data=mtcars, col=as.factor(am), xlim=c(0,30), ylim=c(-30,40), main="1974 Motor Trend Cars", pch=16)

new <- lm(mpg ~ qsec + qsec:am, data=mtcars)

summary(new)

c <- coef(new)
c

abline(c[1], c[2], col=palette()[1])

abline((c[1]), (c[2]+(c[3])), col=palette()[2])

legend("topleft", legend=c("automatic","manual"), pch=1, col=palette(), title="Transmission (am)", bty="n")






palette(c("skyblue","firebrick"))

plot(mpg ~ qsec, data=mtcars, col=as.factor(am), xlim=c(0,30), ylim=c(-30,40), main="1974 Motor Trend Cars", pch=16)

old <- lm(mpg ~ qsec + am + qsec:am, data=mtcars)

summary(old)

b <- coef(old)
b

abline(b[1], b[2], col=palette()[1])

abline((b[1]+b[3]), (b[2]+b[4]), col=palette()[2])

legend("topleft", legend=c("automatic","manual"), pch=1, col=palette(), title="Transmission (am)", bty="n")
