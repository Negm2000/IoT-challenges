clc
clear
close all

sensor_read = readtable("sensor_read.csv");
deep_sleep = readtable("deep_sleep.csv");
transmission_power = readtable("transmission_power.csv");

% Threshold ranges estimated visually from plots
booting = isbetween(deep_sleep.Data,320,450);
sleeping = deep_sleep.Data <= 61;
idle = sensor_read.Data < 333;
scanning = sensor_read.Data > 450;
wifiOn = transmission_power.Data < 710;
tx_2db = isbetween(transmission_power.Data,710,810);
tx_195db = transmission_power.Data > 1000;

% Compute mean power consumption for different states
P_booting = mean(deep_sleep.Data(booting));
P_sleeping = mean(deep_sleep.Data(sleeping));
P_idle = mean(sensor_read.Data(idle));
P_scanning = mean(sensor_read.Data(scanning));
P_wifiOn = mean(transmission_power.Data(wifiOn));
P_tx_2db = mean(transmission_power.Data(tx_2db));
P_tx_19_5db = mean(transmission_power.Data(tx_195db));

% Display results
disp('Power Consumption in Different States:')
disp(['Sleeping: ', num2str(P_sleeping), ' mW'])
disp(['Booting: ', num2str(P_booting), ' mW'])
disp(['Idle: ', num2str(P_idle), ' mW'])
disp(['Scanning: ', num2str(P_scanning), ' mW'])
disp(['Wi-Fi On: ', num2str(P_wifiOn), ' mW'])
disp(['TX 2dB: ', num2str(P_tx_2db), ' mW'])
disp(['TX 19.5dB: ', num2str(P_tx_19_5db), ' mW'])


% ESP32 Power Consumption Duty Cycle

% Empirical data from the ESP32 emulation
boot_time = 0.08;         % seconds
idle_time = 0.001;        % seconds
measure_time = 0.025;     % seconds
wifi_time = 0.192;        % seconds
tx_time = 0.00019;        % seconds [~0.19 ms] 
sleep_time = 25;          % seconds

% Calculate and display summary statistics

% Energy consumption data
boot_energy = P_booting/1000 * boot_time;
idle_energy = P_idle/1000 * idle_time;
measure_energy = P_scanning/1000 * measure_time;
wifi_energy = P_wifiOn/1000 * wifi_time;
tx_energy = P_tx_19_5db/1000 * tx_time;
sleep_energy = P_sleeping/1000 * sleep_time;

%% Q2
energy_values = [boot_energy, idle_energy,measure_energy,wifi_energy,tx_energy,sleep_energy];
durations = [boot_time, idle_time,measure_time,wifi_time,tx_time,sleep_time];
cycle_energy = sum(energy_values); % energy per cycle
cycle_time = sum(durations);
avg_power = cycle_energy / cycle_time * 1000; % Convert to mW
duty_cycle = (cycle_time - sleep_time) / cycle_time * 100;

battery_energy = mod(3520,5000) + 15000;
cycles = battery_energy/cycle_energy;
total_time = cycles * cycle_time / 3600; % hours

fprintf('\nDuty Cycle Analysis:\n');
fprintf('Total cycle time: %.3f seconds\n', cycle_time);
fprintf('Active time: %.3f seconds\n', cycle_time - sleep_time);
fprintf('Duty cycle: %.2f%%\n', duty_cycle);
fprintf('Total energy per cycle: %.3f J\n', cycle_energy);
fprintf('Average power consumption: %.2f mW\n', avg_power);
fprintf('Time the sensor node lasts before changing the battery: %.2f', total_time);

%% Q4
% Sensor coordinates (x, y)
sensors = [1 2; 10 3; 4 8; 15 7; 6 1; 9 12; 14 4; 3 10; 7 7; 12 14];

% Part A: Lifetime with Sink at (20,20)
sink_A = [20, 20];
d_sq_A = sum((sensors - sink_A).^2, 2);        % Squared distances
E_per_packet_A = (50 + d_sq_A) * 2000;         % Energy per packet (nJ)
num_packets_A = 5e6 ./ E_per_packet_A;         % Total packets per sensor
lifetimes_A = num_packets_A * 10;              % Lifetime in minutes
system_lifetime_A = min(lifetimes_A);          % System lifetime

fprintf('\nA. System lifetime with sink at (20,20): %.1f minutes\n', system_lifetime_A);

% Part B: Optimal Sink Position
% Objective: Minimize the maximum squared distance to sensors
fun = @(pos) sum((sensors - pos).^2, 2);       % Returns d² for each sensor
initial_guess = mean(sensors);                 % Start with centroid
options = optimoptions('fminimax', 'Display', 'off');
[opt_pos, max_d_sq] = fminimax(fun, initial_guess, [], [], [], [], [], [], [], options);

% Calculate system lifetime at optimal position
E_per_packet_B = (50 + max(max_d_sq)) * 2000;  % Worst-case energy
num_packets_B = 5e6 / E_per_packet_B;          % Packets for worst sensor
system_lifetime_B = num_packets_B * 10;        % System lifetime

fprintf('B. Optimal sink position: (%.1f, %.1f)\n', opt_pos(1), opt_pos(2));
fprintf('   System lifetime: %.2f minutes\n', system_lifetime_B);


%% Data Vizualization

figure;
subplot(3,1,1);
plot(sensor_read,"Timestamp","Data");
title("Sensor Read")
subplot(3,1,2);
plot(deep_sleep,"Timestamp","Data");
title("Deep Sleep")
subplot(3,1,3);
plot(transmission_power,"Timestamp","Data");
title("Transmission Power")

figure
% States in the duty cycle
operations = {'Booting', 'Idle', 'Measuring', 'Wi-Fi On', 'Transmitting', 'Sleeping'};
% Create a bar chart for energy consumption
subplot(2, 1, 1);
bar(energy_values, 'FaceColor', [0.8, 0.4, 0.2]);
set(gca, 'XTick', 1:length(operations), 'XTickLabel', operations);
title('Energy Consumption per Operation');
ylabel('Energy (J)');
xtickangle(45);
grid on;


% Create a pie chart for time distribution (logarithmic scale for visualization)
% Create figure
subplot(2,1,2)
percentages = energy_values / cycle_energy * 100;
pie(energy_values,repmat({''},size(energy_values)));
title('Energy Distribution');
legend(sprintf('%s (%.2f%%)', operations{1}, percentages(1)), ...
       sprintf('%s (%.2f%%)', operations{2}, percentages(2)), ...
       sprintf('%s (%.2f%%)', operations{3}, percentages(3)), ...
       sprintf('%s (%.2f%%)', operations{4}, percentages(4)), ...
       sprintf('%s (%.2f%%)', operations{5}, percentages(5)), ...
       sprintf('%s (%.2f%%)', operations{6}, percentages(6)), ...
       'Location', 'eastoutside', 'TextColor', 'w', 'FontSize', 12);
colormap(parula);
set(gca, 'Color', 'k');


% Create time and power vectors to plot the power consumption over time
% We'll create a high-resolution time vector to accurately represent the transitions
resolution = 1000000; % Number of points to use for visualization
time = linspace(0, cycle_time, resolution);
power = zeros(size(time));

% Set power values for each time segment
% First, find time indices for each segment boundary
t_boot_end = boot_time;
t_idle_end = t_boot_end + idle_time;
t_measure_end = t_idle_end + measure_time;
t_wifi_end = t_measure_end + wifi_time;
t_tx_end = t_wifi_end + tx_time;

% Assign power values to each time segment
boot_idx = time <= t_boot_end;
power(boot_idx) = P_booting;

idle_idx = (time > t_boot_end) & (time <= t_idle_end);
power(idle_idx) = P_idle;

measure_idx = (time > t_idle_end) & (time <= t_measure_end);
power(measure_idx) = P_scanning;

wifi_idx = (time > t_measure_end) & (time <= t_wifi_end);
power(wifi_idx) = P_wifiOn;

tx_idx = (time > t_wifi_end) & (time <= t_tx_end);
power(tx_idx) = P_tx_19_5db;

sleep_idx = time > t_tx_end;
power(sleep_idx) = P_sleeping;

% Create the figure
figure('Position', [100, 100, 1200, 800]);

% Plot full cycle with sleep
subplot(2, 1, 1);
plot(time, power, 'LineWidth', 2);
grid on;
title('Complete Power Consumption Cycle');
xlabel('Time (seconds)');
ylabel('Power Consumption (mW)');
ylim([0, 1300]);
xlim([0, cycle_time]);

% Annotate the different operating states
text(sleep_time/2, P_sleeping+50, 'Sleep Mode', 'HorizontalAlignment', 'center');

% Add a vertical line to show transition from active to sleep
line([t_tx_end, t_tx_end], [0, 1300], 'Color', 'r', 'LineStyle', '--');
text(t_tx_end+0.2, 1200, 'Active → Sleep Transition', 'Color', 'r');

% Plot zoomed in on the active part
subplot(2, 1, 2);
active_time = time(time <= t_tx_end);
active_power = power(time <= t_tx_end);
plot(active_time, active_power, 'LineWidth', 2);
grid on;
title('Zoomed Power Consumption (Active Period Only)');
xlabel('Time (seconds)');
ylabel('Power Consumption (mW)');
ylim([0, 1300]);

% Add vertical lines to separate the different phases
line([t_boot_end, t_boot_end], [0, 1300], 'Color', 'k', 'LineStyle', '--');
line([t_idle_end, t_idle_end], [0, 1300], 'Color', 'k', 'LineStyle', '--');
line([t_measure_end, t_measure_end], [0, 1300], 'Color', 'k', 'LineStyle', '--');
line([t_wifi_end, t_wifi_end], [0, 1300], 'Color', 'k', 'LineStyle', '--');

% Label the different regions
text(boot_time/2, P_booting+50, 'Booting', 'HorizontalAlignment', 'center');
text(t_boot_end + idle_time/2, P_idle+50, 'Idle', 'HorizontalAlignment', 'center');
text(t_idle_end + measure_time/2, P_scanning+50, 'Scanning', 'HorizontalAlignment', 'center');
text(t_measure_end + wifi_time/2, P_wifiOn+50, 'Wi-Fi On', 'HorizontalAlignment', 'center');
text(t_wifi_end + tx_time/2, P_tx_19_5db+50, 'TX 19.5dB', 'HorizontalAlignment', 'center');

% Add timing durations at the bottom
text(boot_time/2, 120, [num2str(boot_time*1000) ' ms'], 'HorizontalAlignment', 'center');
text(t_boot_end + idle_time/2, 120, [num2str(idle_time*1000) ' ms'], 'HorizontalAlignment', 'center');
text(t_idle_end + measure_time/2, 120, [num2str(measure_time*1000) ' ms'], 'HorizontalAlignment', 'center');
text(t_measure_end + wifi_time/2, 120, [num2str(wifi_time*1000) ' ms'], 'HorizontalAlignment', 'center');
text(t_wifi_end + tx_time/2, 120, [num2str(tx_time*1000) ' ms'], 'HorizontalAlignment', 'center');
