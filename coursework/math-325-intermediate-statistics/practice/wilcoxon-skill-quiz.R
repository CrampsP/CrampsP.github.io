library(tidyverse)

Honda_mpg <- data.frame(date = c("06/01/20", "08/19/20", "09/14/20", "01/07/21", "07/22/21", "08/16/21", "10/24/21", "12/31/21", "03/12/22", "05/04/22", "07/09/22", "10/12/22"), milesDriven = c(274.4, 266.8, 317.0, 113.4, 326.2, 62.6, 239.8, 242.0, 195.6, 106.4, 379.3, 325.4), gallonsUsed = c(12.42, 12.255, 15.224, 7.953, 16.378, 3.285, 13.230, 10.467, 9.310, 4.721, 16.958, 16.221))

View(Honda_mpg)


Honda_mpg <- Honda_mpg %>%
  mutate(mpg = milesDriven / gallonsUsed)


ggplot(Honda_mpg, aes(x=mpg)) +
  geom_dotplot(binwidth = .1) +
  geom_segment(aes(x=17, xend=17, y=0, yend=0.5), color="skyblue") +
  geom_text(aes(x=17, y=.6), label="Median Hypothesized to be 17 mpg", color="skyblue") +
  labs(title="2010 Honda Odyssey Gas Mileages", y="", x="Miles Per Gallon Vehicle Achieved on Systematically Selected Dates") +
  theme(axis.ticks.y=element_blank(), axis.text.y=element_blank())

Honda_mpg$mpg - 17

wilcox.test(Honda_mpg$mpg, mu = 17, alternative = "two.sided")

