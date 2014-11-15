library ieee;
use ieee.std_logic_1164.all;
use work.video_bus.all;
use work.ram_port.all;

entity toplevel is
    port (
        clk_100MHz : in std_logic;
        rst_n : in std_logic;
        rx_tmds : in std_logic_vector(3 downto 0);
        rx_tmdsb : in std_logic_vector(3 downto 0);
        tx_tmds : out std_logic_vector(3 downto 0);
        tx_tmdsb : out std_logic_vector(3 downto 0);
        rx_sda : inout std_logic;
        rx_scl : inout std_logic;
        led : out std_logic_vector(0 downto 0);
        
        mcb3_dram_dq                            : inout  std_logic_vector(16-1 downto 0);
        mcb3_dram_a                             : out std_logic_vector(13-1 downto 0);
        mcb3_dram_ba                            : out std_logic_vector(3-1 downto 0);
        mcb3_dram_ras_n                         : out std_logic;
        mcb3_dram_cas_n                         : out std_logic;
        mcb3_dram_we_n                          : out std_logic;
        mcb3_dram_odt                           : out std_logic;
        mcb3_dram_cke                           : out std_logic;
        mcb3_dram_dm                            : out std_logic;
        mcb3_dram_udqs                          : inout  std_logic;
        mcb3_dram_udqs_n                        : inout  std_logic;
        mcb3_rzq                                : inout  std_logic;
        mcb3_zio                                : inout  std_logic;
        mcb3_dram_udm                           : out std_logic;
        c3_sys_clk                              : in  std_logic;
        c3_sys_rst_i                            : in  std_logic;
        c3_calib_done                           : out std_logic;
        c3_clk0                                 : out std_logic;
        c3_rst0                                 : out std_logic;
        mcb3_dram_dqs                           : inout  std_logic;
        mcb3_dram_dqs_n                         : inout  std_logic;
        mcb3_dram_ck                            : out std_logic;
        mcb3_dram_ck_n                          : out std_logic);
end entity toplevel;


architecture RTL of toplevel is
    signal clk_132MHz : std_logic;
    signal pattern_gen_video_out : video_bus;
    signal mux_video_out, dvi_rx_video_out : video_bus;
    signal rst : std_logic;
    signal combiner_video_out : video_bus;
    signal combiner_video_under_in : video_data;
    
    signal c3_p0_in : ram_port_in;
    signal c3_p0_out : ram_port_out;
begin
    u_dram : entity work.dram port map (
        c3_sys_clk  =>         c3_sys_clk,
        c3_sys_rst_i    =>       c3_sys_rst_i,                        
        mcb3_dram_dq       =>    mcb3_dram_dq,  
        mcb3_dram_a        =>    mcb3_dram_a,  
        mcb3_dram_ba       =>    mcb3_dram_ba,
        mcb3_dram_ras_n    =>    mcb3_dram_ras_n,                        
        mcb3_dram_cas_n    =>    mcb3_dram_cas_n,                        
        mcb3_dram_we_n     =>    mcb3_dram_we_n,                          
        mcb3_dram_odt    =>      mcb3_dram_odt,
        mcb3_dram_cke      =>    mcb3_dram_cke,                          
        mcb3_dram_ck       =>    mcb3_dram_ck,                          
        mcb3_dram_ck_n     =>    mcb3_dram_ck_n,       
        mcb3_dram_dqs      =>    mcb3_dram_dqs,                          
        mcb3_dram_dqs_n  =>      mcb3_dram_dqs_n,
        mcb3_dram_udqs  =>       mcb3_dram_udqs,    -- for X16 parts           
        mcb3_dram_udqs_n    =>   mcb3_dram_udqs_n,  -- for X16 parts
        mcb3_dram_udm  =>        mcb3_dram_udm,     -- for X16 parts
        mcb3_dram_dm  =>       mcb3_dram_dm,
        c3_clk0    =>            c3_clk0,
        c3_rst0        =>        c3_rst0,
        c3_calib_done      =>    c3_calib_done,
        mcb3_rzq        =>            mcb3_rzq,
        mcb3_zio        =>            mcb3_zio,
        c3_p0_cmd_clk                           =>  c3_p0_in.cmd_clk,
        c3_p0_cmd_en                            =>  c3_p0_in.cmd_en,
        c3_p0_cmd_instr                         =>  c3_p0_in.cmd_instr,
        c3_p0_cmd_bl                            =>  c3_p0_in.cmd_bl,
        c3_p0_cmd_byte_addr                     =>  c3_p0_in.cmd_byte_addr,
        c3_p0_cmd_empty                         =>  c3_p0_out.cmd_empty,
        c3_p0_cmd_full                          =>  c3_p0_out.cmd_full,
        c3_p0_wr_clk                            =>  c3_p0_in.wr_clk,
        c3_p0_wr_en                             =>  c3_p0_in.wr_en,
        c3_p0_wr_mask                           =>  c3_p0_in.wr_mask,
        c3_p0_wr_data                           =>  c3_p0_in.wr_data,
        c3_p0_wr_full                           =>  c3_p0_out.wr_full,
        c3_p0_wr_empty                          =>  c3_p0_out.wr_empty,
        c3_p0_wr_count                          =>  c3_p0_out.wr_count,
        c3_p0_wr_underrun                       =>  c3_p0_out.wr_underrun,
        c3_p0_wr_error                          =>  c3_p0_out.wr_error,
        c3_p0_rd_clk                            =>  c3_p0_in.rd_clk,
        c3_p0_rd_en                             =>  c3_p0_in.rd_en,
        c3_p0_rd_data                           =>  c3_p0_out.rd_data,
        c3_p0_rd_full                           =>  c3_p0_out.rd_full,
        c3_p0_rd_empty                          =>  c3_p0_out.rd_empty,
        c3_p0_rd_count                          =>  c3_p0_out.rd_count,
        c3_p0_rd_overflow                       =>  c3_p0_out.rd_overflow,
        c3_p0_rd_error                          =>  c3_p0_out.rd_error,
        c3_p1_cmd_clk                           =>  c3_p1_cmd_clk,
        c3_p1_cmd_en                            =>  c3_p1_cmd_en,
        c3_p1_cmd_instr                         =>  c3_p1_cmd_instr,
        c3_p1_cmd_bl                            =>  c3_p1_cmd_bl,
        c3_p1_cmd_byte_addr                     =>  c3_p1_cmd_byte_addr,
        c3_p1_cmd_empty                         =>  c3_p1_cmd_empty,
        c3_p1_cmd_full                          =>  c3_p1_cmd_full,
        c3_p1_wr_clk                            =>  c3_p1_wr_clk,
        c3_p1_wr_en                             =>  c3_p1_wr_en,
        c3_p1_wr_mask                           =>  c3_p1_wr_mask,
        c3_p1_wr_data                           =>  c3_p1_wr_data,
        c3_p1_wr_full                           =>  c3_p1_wr_full,
        c3_p1_wr_empty                          =>  c3_p1_wr_empty,
        c3_p1_wr_count                          =>  c3_p1_wr_count,
        c3_p1_wr_underrun                       =>  c3_p1_wr_underrun,
        c3_p1_wr_error                          =>  c3_p1_wr_error,
        c3_p1_rd_clk                            =>  c3_p1_rd_clk,
        c3_p1_rd_en                             =>  c3_p1_rd_en,
        c3_p1_rd_data                           =>  c3_p1_rd_data,
        c3_p1_rd_full                           =>  c3_p1_rd_full,
        c3_p1_rd_empty                          =>  c3_p1_rd_empty,
        c3_p1_rd_count                          =>  c3_p1_rd_count,
        c3_p1_rd_overflow                       =>  c3_p1_rd_overflow,
        c3_p1_rd_error                          =>  c3_p1_rd_error,
        c3_p2_cmd_clk                           =>  c3_p2_cmd_clk,
        c3_p2_cmd_en                            =>  c3_p2_cmd_en,
        c3_p2_cmd_instr                         =>  c3_p2_cmd_instr,
        c3_p2_cmd_bl                            =>  c3_p2_cmd_bl,
        c3_p2_cmd_byte_addr                     =>  c3_p2_cmd_byte_addr,
        c3_p2_cmd_empty                         =>  c3_p2_cmd_empty,
        c3_p2_cmd_full                          =>  c3_p2_cmd_full,
        c3_p2_wr_clk                            =>  c3_p2_wr_clk,
        c3_p2_wr_en                             =>  c3_p2_wr_en,
        c3_p2_wr_mask                           =>  c3_p2_wr_mask,
        c3_p2_wr_data                           =>  c3_p2_wr_data,
        c3_p2_wr_full                           =>  c3_p2_wr_full,
        c3_p2_wr_empty                          =>  c3_p2_wr_empty,
        c3_p2_wr_count                          =>  c3_p2_wr_count,
        c3_p2_wr_underrun                       =>  c3_p2_wr_underrun,
        c3_p2_wr_error                          =>  c3_p2_wr_error,
        c3_p3_cmd_clk                           =>  c3_p3_cmd_clk,
        c3_p3_cmd_en                            =>  c3_p3_cmd_en,
        c3_p3_cmd_instr                         =>  c3_p3_cmd_instr,
        c3_p3_cmd_bl                            =>  c3_p3_cmd_bl,
        c3_p3_cmd_byte_addr                     =>  c3_p3_cmd_byte_addr,
        c3_p3_cmd_empty                         =>  c3_p3_cmd_empty,
        c3_p3_cmd_full                          =>  c3_p3_cmd_full,
        c3_p3_rd_clk                            =>  c3_p3_rd_clk,
        c3_p3_rd_en                             =>  c3_p3_rd_en,
        c3_p3_rd_data                           =>  c3_p3_rd_data,
        c3_p3_rd_full                           =>  c3_p3_rd_full,
        c3_p3_rd_empty                          =>  c3_p3_rd_empty,
        c3_p3_rd_count                          =>  c3_p3_rd_count,
        c3_p3_rd_overflow                       =>  c3_p3_rd_overflow,
        c3_p3_rd_error                          =>  c3_p3_rd_error);

    rst <= not rst_n;
    
    U_DVI_RX : entity work.dvi_receiver
        port map(rst          => rst,
                 rx_tmds      => rx_tmds,
                 rx_tmdsb     => rx_tmdsb,
                 video_output => dvi_rx_video_out);
    
    led(0) <= dvi_rx_video_out.sync.valid;
    
    U_PIXEL_CLK_GEN : entity work.pixel_clk_gen
        port map(CLK_IN1  => clk_100MHz,
                 CLK_OUT1 => clk_132MHz,
                 RESET    => '0',
                 LOCKED   => open);
    
    U_PATTERN_GEN : entity work.video_pattern_generator
        port map(
                reset => rst,
                clk_in => clk_132MHz,
                video  => pattern_gen_video_out);
                
    combiner_video_under_in.blue <= x"FF";
    combiner_video_under_in.red <= x"00";
    combiner_video_under_in.green <= x"00";                

    U_OVERLAY : entity work.video_overlay
        port map(video_over  => pattern_gen_video_out.data,
                 video_under => combiner_video_under_in,
                 video_out   => combiner_video_out.data);
                 
    combiner_video_out.sync <= pattern_gen_video_out.sync;
 
    U_SRC_MUX : entity work.video_mux
        port map(video0    => combiner_video_out,
                 video1    => dvi_rx_video_out,
                 sel       => dvi_rx_video_out.sync.valid,
                 video_out => mux_video_out);        
                 
    U_DVI_TX : entity work.dvi_transmitter
        port map(video_in => mux_video_out,
                 tx_tmds  => tx_tmds,
                 tx_tmdsb => tx_tmdsb);  
 
    U_EDID : entity work.edid_wrapper
        port map(clk_132MHz => clk_132MHz,
                 reset        => rst,
                 scl        => rx_scl,
                 sda        => rx_sda);
                 
end architecture RTL;
