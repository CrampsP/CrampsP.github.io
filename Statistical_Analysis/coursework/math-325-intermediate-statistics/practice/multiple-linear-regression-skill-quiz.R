library(mosaic)
?SaratogaHouses
SH2 <- filter(SaratogaHouses, bedrooms == 3,  newConstruction=="Yes")

View(SH2)
sh2.lm <- lm(price ~ livingArea + fireplaces + livingArea:fireplaces, data = SH2)
summary(sh2.lm)

plot(price ~ livingArea + fireplaces + livingArea:fireplaces, data = SH2)

View(airquality)
lm.quad <-lm(Temp ~ Month + I(Month^2), data=airquality)
summary(lm.quad)
plot(lm.quad)
-95.73+48.72*(7.129032)+-3.283*(7.129032)*(7.129032)


b <- coef(lm.quad)
b
plot(Temp ~ Month, data = airquality)

curve(b[1]+b[2]*x+b[3]*x*x, add=TRUE, col="skyblue2", lwd=2)

lines(c(7.4, 7.4), c(0, 85), lty=2, col="firebrick")

lines(c(0, 7.5), c(85, 85), lty=2, col="firebrick")

points(7.4, 85, cex=1.2, col="red")

text(7.4, 85, "Predicted Temp", cex=0.5, pos=3)

library(mosaic)
?RailTrail
View(RailTrail)

RailTrail <- RailTrail %>%
  mutate(rain = ifelse(precip > 0, 1, 0))

palette(c("orange","skyblue"))
plot(volume ~ hightemp, data=RailTrail, col=as.factor(rain), main="RailTrail Data Set")
legend("topleft", legend=c("No Rain", "Rain"), col=palette(), pch=16)


full.lm <- lm(volume ~ hightemp * rain, data = RailTrail)
summary(full.lm)


